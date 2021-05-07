import React, { Component } from 'react'

import { baseUrl } from '../../config';
import axios from 'axios';
import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap4.min.css"; // use Theme(s)
<<<<<<< HEAD
<<<<<<< HEAD
import { ReactTabulator } from 'react-tabulator'
=======
import { ReactTabulator, reactFormatter } from 'react-tabulator'
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
import { ReactTabulator } from 'react-tabulator'
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
import {Container, Row, Col} from 'react-bootstrap'


export class Threats extends Component {
    constructor(props) {
        super(props)
    
        this.state = {
             threatsData: []
        }
    }

    componentDidMount() {
        axios.get(baseUrl + 'api/v1/tables/threats')
            .then(response => {
                this.setState({
                    threatsData : response.data
                });
            })
            .catch(function(error) {
                console.log(error);
            })
        }
    
    render() {
        const columns = [
            { title: "Host", field: "host"},
            { title: "Severity", field: "severity"},
            { title: "Message", field: "message"},
          ];
          const options = {
            movableRows: true,
<<<<<<< HEAD
<<<<<<< HEAD
            movableColumns: true,
            paginationSize:10,
            pagination:"local"
=======
            movableColumns: true
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
            movableColumns: true,
            paginationSize:10,
            pagination:"local"
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
          };

        return (
            <div>
            <Container>
            <Row className="show-grid">
                <Col md={{ span: 8, offset: 2}}>
                <div>
                <h1 style={{marginLeft: '350px', fontSize: 26, fontWeight: 'bold', marginBottom: '20px'}}>Threats Data</h1>
                <ReactTabulator
                    data={this.state.threatsData}
                    columns={columns}
                    tooltips={true}
                    options={options}
                    data-custom-attr="test-custom-attribute"
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    className="table-active table-light thead-dark table-striped table-primary table-bordered "          
                    />
                </div>
                </Col>
                </Row>
            </Container>
            </div>
        )
    }
}

export default Threats;
