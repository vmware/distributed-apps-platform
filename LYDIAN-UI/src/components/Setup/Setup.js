import React, { Component } from 'react'
import { Card, Col, Row} from 'antd';
import axios from 'axios';
import { Redirect } from 'react-router-dom';
import { baseUrl } from '../../config';

import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap4.min.css"; // use Theme(s)
import { ReactTabulator, reactFormatter } from 'react-tabulator'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { library } from "@fortawesome/fontawesome-svg-core";
import {faApple, faWindows, faUbuntu} from "@fortawesome/free-brands-svg-icons"

library.add(faWindows);
library.add(faUbuntu);
library.add(faApple);



export class Setup extends Component {
    constructor(props) {
        super(props)
    
        this.state = {
            primarydata: [],
            endpointsdata: [],
            selectedendpoint: '',
        }
    }


    componentDidMount() {
        axios.get(baseUrl + 'api/v1/tables/runner')
            .then(response => {
                this.setState({
                    primarydata : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        axios.get(baseUrl + 'api/v1/tables/endpoints')
            .then(response => {
                this.setState({
                    endpointsdata : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        }
    
    ref: any = null;

    rowClick = (e: any, row: any) => {
            console.log('ref table: ', this.ref.table); // this is the Tabulator table instance
            console.log('rowClick id: ${row.getData().id}', row, e);
            this.setState({ selectedendpoint: row.getData().endpoint });
          };
    
  
        
    render() {
        const IconFormatter = (e) => {
            const rowData = e.cell._cell.row.data;
            return(
                <div>
                {rowData.host_type == 'MAC' ? 
                (
                    <FontAwesomeIcon
                    icon={faApple}
                    size='2x'
                    />
                ) :
                ((rowData.host_type == 'LINUX' ? 
                (
                    <FontAwesomeIcon
                    icon={faUbuntu}
                    size='2x'
                    />
                ) :
                (
                    <div>
                    <FontAwesomeIcon
                    icon={faWindows}
                    size='2x'
                    />
                    </div>
                )))
                }
                
                </div>
                )
        }
        const endpointcolumns = [
            { title: "Endpoint", field: "endpoint", headerFilter:true},
            { title: "Hostname", field: "hostname"},
            { title: "Host Type", field: "host_type", align: "center", formatter: reactFormatter(<IconFormatter />)},
            { title: "Mgmt IP", field: "mgmt_ip"},
            { title: "Mgmt Mac", field: "mgmt_mac"}
        ];
        const options = {
            movableRows: true,
            paginationSize:5,
            layout:"fitColumns",
            pagination:"local",
            movableColumns: true
          };

        const primaryColumns = [
            { title: "Primary IP", field: "ip"},
            { title: "Hostname", field: "hostname"},
            { title: "VIF", field: "vif"},
        ];
        const primaryoptions = {
            movableRows: true,
            movableColumns: true,
            layout: "fitColumns"
        }
        
        
        return (
            <div>
            <Row style={{paddingBottom: 30}}>
            <Col style={{marginLeft: '220px'}} md={{ span: 10, offset:  1}}>
                <div>
                <h1 style={{textAlign:'center', fontSize: 22, fontWeight: 'bold', marginBottom: '20px'}}>Primary Node Info</h1>
                <ReactTabulator 
                    data={this.state.primarydata}
                    columns={primaryColumns}
                    tooltips={true}
                    options={primaryoptions}
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    data-custom-attr="test-custom-attribute"
                    className="table-active table-light thead-dark table-striped table-primary table-bordered"                 
                />
                </div>
                </Col>

            </Row>
            <Row>
            <label style={{marginLeft: '350px', fontSize: 22, fontWeight: 'bold', marginBottom: '20px'}}>Endpoints Data</label>
            <ReactTabulator
                    ref={(ref) => (this.ref = ref)}
                    rowClick={this.rowClick}    
                    data={this.state.endpointsdata}
                    columns={endpointcolumns}
                    tooltips={true}
                    options={options}
                    data-custom-attr="test-custom-attribute"
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    className="table-active table-light thead-dark table-striped table-primary table-bordered"          
                    />
            </Row>
            <div>
            {this.state.selectedendpoint ? (
                            <Redirect to={{
                                pathname:'/Endpoint',
                                state: { endpoint: this.state.selectedendpoint }
                            }}/>
                
            ) : (
                <div>
                </div>
            )}
            </div>
            </div>
        )
    }
}

export default Setup
