import React, { Component } from 'react'
<<<<<<< HEAD
<<<<<<< HEAD
import { Col, Row} from 'antd';
=======
import { Card, Col, Row} from 'antd';
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
import { Col, Row} from 'antd';
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
import axios from 'axios';
import { Redirect } from 'react-router-dom';
import { baseUrl } from '../../config';

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
import { useContext, useState, useEffect, useRef } from 'react';
import { Table, Input, Form } from 'antd';


<<<<<<< HEAD
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
import "react-tabulator/lib/styles.css"; // default theme
import "react-tabulator/css/bootstrap/tabulator_bootstrap4.min.css"; // use Theme(s)
import { ReactTabulator, reactFormatter } from 'react-tabulator'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { library } from "@fortawesome/fontawesome-svg-core";
import {faApple, faWindows, faUbuntu} from "@fortawesome/free-brands-svg-icons"
<<<<<<< HEAD
<<<<<<< HEAD
import {faPencilAlt} from "@fortawesome/free-solid-svg-icons"
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
import {faPencilAlt} from "@fortawesome/free-solid-svg-icons"
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node

library.add(faWindows);
library.add(faUbuntu);
library.add(faApple);
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
library.add(faPencilAlt)

const EditableContext = React.createContext(null);

const EditableRow = ({ index, ...props }) => {
    const [form] = Form.useForm();
    return (
      <Form form={form} component={false}>
        <EditableContext.Provider value={form}>
          <tr {...props} />
        </EditableContext.Provider>
      </Form>
    );
  };

const EditableCell = ({
    title,
    editable,
    children,
    dataIndex,
    record,
    handleSave,
    ...restProps
  }) => {
    const [editing, setEditing] = useState(false);
    const inputRef = useRef(null);
    const form = useContext(EditableContext);
    useEffect(() => {
      if (editing && record.key === "IP") {
        inputRef.current.focus();
      }
    }, [editing, record]);
<<<<<<< HEAD

    const toggleEdit = () => {
      setEditing(!editing);
      form.setFieldsValue({
        [dataIndex]: record[dataIndex],
      });
    };

    const save = async () => {
      try {
        console.log("__________________________")
        console.log(record)
        const values = await form.validateFields();
        toggleEdit();
        handleSave({ ...record, ...values });
      } catch (errInfo) {
        console.log('Save failed:', errInfo);
      }
    };

    let childNode = children;

=======

    const toggleEdit = () => {
      setEditing(!editing);
      form.setFieldsValue({
        [dataIndex]: record[dataIndex],
      });
    };

    const save = async () => {
      try {
        console.log("__________________________")
        console.log(record)
        const values = await form.validateFields();
        toggleEdit();
        handleSave({ ...record, ...values });
      } catch (errInfo) {
        console.log('Save failed:', errInfo);
      }
    };

    let childNode = children;

>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
    if (editable) {
      childNode = editing && record.key === "IP" ? (
        <Form.Item
          style={{
            margin: 0,
          }}
          name={dataIndex}
          rules={[
            {
              required: true,
              message: `${title} is required.`,
            },
          ]}
        >
          <Input ref={inputRef} onPressEnter={save} onBlur={save} />
        </Form.Item>
      ) : (
        <div
          className="editable-cell-value-wrap"
          style={{
            paddingRight: 24,
          }}
          onClick={toggleEdit}
        >
          {children}
        </div>
      );
    }
<<<<<<< HEAD

    return <td {...restProps}>{childNode}</td>;
  };
=======
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node

    return <td {...restProps}>{childNode}</td>;
  };

>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021

export class Setup extends Component {
    constructor(props) {
        super(props)
    
        this.state = {
            primarydata: [],
            endpointsdata: [],
            selectedendpoint: '',
<<<<<<< HEAD
<<<<<<< HEAD
            dataSource: '',
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
            dataSource: '',
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
        }
    }


    componentDidMount() {
        axios.get(baseUrl + 'api/v1/tables/runner')
            .then(response => {
<<<<<<< HEAD
<<<<<<< HEAD
                console.log(response.data)
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
                console.log(response.data)
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node

    ChangeData = (data) => {
        axios.post(baseUrl + 'tables/runner',{ crossdomain: true }, data)
            .then(response => {
                console.log(response)
            })
            .catch(function(error) {
                console.log(error);
            })
    }
<<<<<<< HEAD
=======
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
    
    ref: any = null;

    rowClick = (e: any, row: any) => {
            console.log('ref table: ', this.ref.table); // this is the Tabulator table instance
<<<<<<< HEAD
<<<<<<< HEAD
            this.setState({ selectedendpoint: row.getData().endpoint });
          };

    handleSave = (row) => {
        this.ChangeData(row)
        const newData = [...this.state.primarydata];
        const index = newData.findIndex((item) => row.key === item.key);
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        this.setState({
            primarydata: newData,
        });
    };


=======
            console.log('rowClick id: ${row.getData().id}', row, e);
            this.setState({ selectedendpoint: row.getData().endpoint });
          };
    
  
        
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
            this.setState({ selectedendpoint: row.getData().endpoint });
          };

    handleSave = (row) => {
        this.ChangeData(row)
        const newData = [...this.state.primarydata];
        const index = newData.findIndex((item) => row.key === item.key);
        const item = newData[index];
        newData.splice(index, 1, { ...item, ...row });
        this.setState({
            primarydata: newData,
        });
    };


>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
    render() {
        const IconFormatter = (e) => {
            const rowData = e.cell._cell.row.data;
            return(
                <div>
<<<<<<< HEAD
<<<<<<< HEAD
                {rowData.host_type === 'MAC' ?
=======
                {rowData.host_type == 'MAC' ? 
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
                {rowData.host_type === 'MAC' ?
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
                (
                    <FontAwesomeIcon
                    icon={faApple}
                    size='2x'
                    />
                ) :
<<<<<<< HEAD
<<<<<<< HEAD
                ((rowData.host_type === 'UBUNTU' ?
=======
                ((rowData.host_type == 'LINUX' ? 
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
                ((rowData.host_type === 'UBUNTU' ?
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
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
<<<<<<< HEAD
<<<<<<< HEAD
            { title: "Host Type", field: "host_type", formatter: reactFormatter(<IconFormatter />)},
            { title: "Mgmt Ifname", field: "mgmt_ifname"},
=======
            { title: "Host Type", field: "host_type", align: "center", formatter: reactFormatter(<IconFormatter />)},
            { title: "Mgmt IP", field: "mgmt_ip"},
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
            { title: "Host Type", field: "host_type", formatter: reactFormatter(<IconFormatter />)},
            { title: "Mgmt Ifname", field: "mgmt_ifname"},
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
            { title: "Mgmt Mac", field: "mgmt_mac"}
        ];
        const options = {
            movableRows: true,
<<<<<<< HEAD
<<<<<<< HEAD
            paginationSize:10,
            responsiveLayout:"hide",
=======
            paginationSize:5,
            layout:"fitColumns",
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
            paginationSize:10,
            responsiveLayout:"hide",
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
            pagination:"local",
            movableColumns: true
          };

        const primaryColumns = [
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
            { title: "Key", key: "key", dataIndex: "key"},
            { title: "Value", key: "value", dataIndex: "value", editable: true,
              render: (value, record) => (
                  record.key === "IP" ?
                  <div>
                    <span>
                    {value} &nbsp; &nbsp; &nbsp;  <FontAwesomeIcon icon={faPencilAlt}/>
                  </span>
                  </div>
                   :
                   <div>
                  <span>
                    {value}
                  </span>
                  </div>
              )},
<<<<<<< HEAD
        ];

          const editablecolumns = primaryColumns.map((col) => {
            if (!col.editable) {
              return col;
            }

            return {
              ...col,
              onCell: (record) => ({
                record,
                editable: col.editable,
                dataIndex: col.dataIndex,
                title: col.title,
                handleSave: this.handleSave,
              }),
            };
          });

          const components = {
            body: {
                row: EditableRow,
                cell: EditableCell,
            },
          };


        return (

=======
            { title: "Primary IP", field: "ip"},
            { title: "Hostname", field: "hostname"},
            { title: "VIF", field: "vif"},
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
        ];

          const editablecolumns = primaryColumns.map((col) => {
            if (!col.editable) {
              return col;
            }

            return {
              ...col,
              onCell: (record) => ({
                record,
                editable: col.editable,
                dataIndex: col.dataIndex,
                title: col.title,
                handleSave: this.handleSave,
              }),
            };
          });

          const components = {
            body: {
                row: EditableRow,
                cell: EditableCell,
            },
          };


        return (
<<<<<<< HEAD
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======

>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
            <div>
            <Row style={{paddingBottom: 30}}>
            <Col style={{marginLeft: '220px'}} md={{ span: 10, offset:  1}}>
                <div>
                <h1 style={{textAlign:'center', fontSize: 22, fontWeight: 'bold', marginBottom: '20px'}}>Primary Node Info</h1>
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
                <Table
                    components={components}
                    columns={editablecolumns}
                    dataSource={this.state.primarydata}
                    bordered
                    rowClassName={() => 'editable-row'}
                    pagination={false}
<<<<<<< HEAD
=======
                <ReactTabulator 
                    data={this.state.primarydata}
                    columns={primaryColumns}
                    tooltips={true}
                    options={primaryoptions}
                    style={{border: "2px solid rgb(0, 0, 0)"}}
                    data-custom-attr="test-custom-attribute"
                    className="table-active table-light thead-dark table-striped table-primary table-bordered"                 
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
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
